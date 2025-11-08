"""
Database simulation for device settings using in-memory DB object

This module provides a simple in-memory database for device settings simulation,
following the same pattern as other APIs in the project.

The database (DB) organizes data under:
- 'device_settings': Contains device configuration settings
- 'device_insights': Contains device analytics and insights  
- 'installed_apps': Contains app notification settings
- 'actions': Contains action history
"""

import json
import os
import sys
from typing import Dict, Any
from common_utils.print_log import print_log

# Default database path
DEFAULT_DB_PATH = os.path.join(
    os.path.dirname(
        os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    ),
    "DBs",
    "DeviceSettingDefaultDB.json",
)

# Load the initial database
DB = None
with open(DEFAULT_DB_PATH, "r", encoding="utf-8") as f:
    DB = json.load(f)


def save_state(filepath: str) -> None:
    """Save the current state to a JSON file.

    Args:
        filepath (str): Path to save the state file.
    """
    try:
        # Ensure the directory exists if filepath includes directories
        dir_name = os.path.dirname(filepath)
        if dir_name:
            os.makedirs(dir_name, exist_ok=True)
            
        with open(filepath, "w", encoding="utf-8") as f:
            json.dump(DB, f)
            
    except IOError as e:
        print_log(f"ERROR: Could not write to {filepath}: {e}", file=sys.stderr)
    except Exception as e:
        print_log(f"An unexpected error occurred while saving state to '{filepath}': {e}", file=sys.stderr)


def load_state(filepath: str) -> None:
    """
    Loads the application state from a specified JSON file, replacing the
    current in-memory 'DB'.

    Args:
        filepath (str): The path to the JSON file from which to load the state.
    """
    global DB  # Declare intent to modify the global DB object
    try:
        with open(filepath, "r", encoding="utf-8") as f:
            loaded_state = json.load(f)
            DB.clear()  # Remove all items from the current DB
            DB.update(loaded_state)  # Populate DB with the loaded state
            
    except FileNotFoundError:
        print_log(f"Warning: State file '{filepath}' not found. Using current or default DB state.", file=sys.stderr)
    except json.JSONDecodeError as e:
        print_log(f"Error: Could not decode JSON from '{filepath}'. DB state may be invalid or outdated. Details: {e}", file=sys.stderr)
    except Exception as e:
        print_log(f"An unexpected error occurred while loading state from '{filepath}': {e}", file=sys.stderr)

def get_minified_state() -> dict:
    """
    Returns a minified version of the current state of the application.
    """
    global DB
    return DB
