from common_utils.print_log import print_log
"""
In-Memory Database for the Generic Service

This module manages the in-memory database for the simulation. It initializes
the database structure, and provides functions for saving, loading, and
resetting its state.
"""

import os
import json
from typing import Dict, Any

# Initialize the database structure. This should match the root Pydantic model
# defined in `models.py`.
DB: Dict[str, Any] = {
    "entities": {},
    # The 'actions' table has been removed for a more generic template.
}

def save_state(filepath: str) -> None:
    """
    Saves the current state of the database to a JSON file.

    Args:
        filepath: The path to the file where the state will be saved.
    """
    # Create the directory if it doesn't exist
    os.makedirs(os.path.dirname(filepath), exist_ok=True)
    with open(filepath, "w") as f:
        json.dump(DB, f, indent=2)

def load_state(filepath: str) -> None:
    """
    Loads the database state from a JSON file.

    If the file is not found, the database remains in its current state.

    Args:
        filepath: The path to the file from which to load the state.
    """
    global DB
    try:
        with open(filepath, "r") as f:
            loaded_data = json.load(f)
            DB.update(loaded_data)
    except FileNotFoundError:
        # It's okay if the state file doesn't exist; we'll just use the default DB.
        pass
    except json.JSONDecodeError:
        print_log(f"Warning: Could not decode JSON from {filepath}. Using default DB.")


def reset_db() -> None:
    """
    Resets the database to its initial empty state.
    """
    global DB
    for key in list(DB.keys()):
        if isinstance(DB[key], dict):
            DB[key].clear()
        elif isinstance(DB[key], list):
            DB[key].clear()

def load_default_data() -> None:
    """
    Loads the default database from the 'DBs' directory.
    
    The filename should follow the pattern 'ServiceNameDefaultDB.json'.
    """
    # TODO: Change 'ServiceTemplateDefaultDB.json' to the actual default DB file name
    # for your new service (e.g., 'CalendarDefaultDB.json').
    db_filename = "ServiceTemplateDefaultDB.json"
    
    db_path = os.path.join(
        # Navigate up three levels from SimulationEngine to the root project directory
        os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(__file__)))),
        "DBs",
        db_filename
    )
    
    if os.path.exists(db_path):
        load_state(db_path)
    else:
        print_log(f"Warning: Default database file not found at {db_path}. Using empty DB.")

# Initialize the database with default data when the module is first imported.
load_default_data()

def get_minified_state() -> dict:
    """
    Returns a minified version of the current state of the application.
    """
    global DB
    return DB
