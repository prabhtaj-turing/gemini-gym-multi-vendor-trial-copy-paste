# instagram/SimulationEngine/db.py

import json
import os


# ------------------------------------------------------------------------------
# Global In-Memory Database (JSON-serializable)
# ------------------------------------------------------------------------------
DB = {"users": {}, "media": {}, "comments": {}}


# def save_state(filepath: str = "state.json") -> None:
#     """Saves the current state of the DB to a JSON file."""
#     # Ensure the directory exists if filepath includes directories
#     dir_name = os.path.dirname(filepath)
#     if dir_name:
#         os.makedirs(dir_name, exist_ok=True)
#     try:
#         with open(filepath, "w") as f:
#             json.dump(DB, f, indent=4)
#     except IOError as e:
#         # Keep error print for save_state as it might indicate permission issues etc.
#         print(f"ERROR in save_state: Could not write to {filepath}: {e}", file=sys.stderr)

# def load_state(filepath: str = "state.json") -> None:
#     """Loads the DB state from a JSON file, overwriting the current state."""
#     global DB # Ensure we are modifying the global DB

#     if os.path.exists(filepath):
#         try:
#             with open(filepath, "r") as f:
#                 loaded_data = json.load(f)

#                 # Basic validation
#                 is_dict = isinstance(loaded_data, dict)
#                 has_keys = is_dict and loaded_data is not None and all(k in loaded_data for k in ["users", "media", "comments"])

#                 if is_dict and has_keys:
#                         # Mutate the existing DB object instead of reassigning the name
#                         DB.clear()
#                         DB.update(loaded_data)
#                 else:
#                         # Handle invalid data structure - reset DB
#                         print(f"Warning: Invalid data structure in {filepath}. Resetting DB.", file=sys.stderr)
#                         DB.clear()
#                         DB.update({"users": {}, "media": {}, "comments": {}})
#         except (json.JSONDecodeError, IOError) as e:
#             # Handle file read or JSON parsing errors - reset DB
#             print(f"Error loading state from {filepath}: {e}. Resetting DB.", file=sys.stderr)
#             DB.clear()
#             DB.update({"users": {}, "media": {}, "comments": {}})
#         except Exception as e:
#             # Catch any other unexpected errors during loading - reset DB
#             print(f"Unexpected error loading state from {filepath}: {e}. Resetting DB.", file=sys.stderr)
#             DB.clear()
#             DB.update({"users": {}, "media": {}, "comments": {}})
#     else:
#         # File does not exist - reset DB to default empty state
#         DB.clear()
#         DB.update({"users": {}, "media": {}, "comments": {}})


def save_state(filepath: str) -> None:
    with open(filepath, "w") as f:
        json.dump(DB, f)


def load_state(filepath: str) -> None:
    global DB
    with open(filepath, "r") as f:
        state = json.load(f)
    # Instead of reassigning DB, update it in place:
    DB.clear()
    DB.update(state)

def get_minified_state() -> dict:
    """
    Returns a minified version of the current state of the application.
    """
    global DB
    return DB
